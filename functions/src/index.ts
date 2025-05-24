import * as functions from "firebase-functions";
import * as admin from "firebase-admin";

// Initialize Firebase Admin SDK
admin.initializeApp();
const firestore = admin.firestore();

/**
 * HTTP function to reset all users' daily token usage
 * Triggered by Cloud Scheduler at midnight UTC daily
 */
export const resetDailyTokenUsage = functions.https.onRequest(
    async (request, response) => {
      try {
        // Verify the request has a valid authorization header if needed
        // This is a simple example - in production you might want to add more security
        const authHeader = request.headers.authorization;
        if (!authHeader || !authHeader.startsWith("Bearer ")) {
          response.status(403).send("Unauthorized");
          return;
        }

        // Get the token from the Authorization header
        const token = authHeader.split("Bearer ")[1];
        
        // In production, validate this token against a secret stored in environment variables
        // For now, we're using a simple check
        const expectedToken = functions.config().scheduler?.token || "default-token-for-dev";
        if (token !== expectedToken) {
          response.status(403).send("Invalid token");
          return;
        }

        // Get current date in YYYY-MM-DD format
        const today = new Date().toISOString().split("T")[0];
        
        // Get all token_usage documents
        const usageDocs = await firestore.collection("token_usage").get();
        
        // Prepare batch writes to reset all daily usage counters
        const batch = firestore.batch();
        let userCount = 0;
        
        usageDocs.forEach((doc) => {
          const userId = doc.id;
          const dailyRef = firestore
              .collection("token_usage")
              .doc(userId)
              .collection("daily")
              .doc(today);
              
          batch.set(dailyRef, {
            tokens_used: 0,
            date: today,
            created_at: admin.firestore.FieldValue.serverTimestamp(),
            last_updated: admin.firestore.FieldValue.serverTimestamp(),
            reset_by: "automated-scheduler",
          });
          
          userCount++;
        });
        
        // Execute batch write
        await batch.commit();
        
        // Log success and respond
        console.log(`Successfully reset token usage for ${userCount} users on ${today}`);
        response.status(200).send({
          success: true,
          message: `Successfully reset token usage for ${userCount} users`,
          date: today,
        });
      } catch (error) {
        console.error("Error resetting token usage:", error);
        response.status(500).send({
          success: false,
          error: `Error: ${error.message}`,
        });
      }
    }
);

/**
 * Scheduled function to reset token usage automatically
 * Runs at midnight UTC daily (cron syntax: 0 0 * * *)
 */
export const scheduledResetTokenUsage = functions.pubsub
    .schedule("0 0 * * *")
    .timeZone("UTC")
    .onRun(async (context) => {
      try {
        // Get current date in YYYY-MM-DD format
        const today = new Date().toISOString().split("T")[0];
        
        // Get all token_usage documents
        const usageDocs = await firestore.collection("token_usage").get();
        
        // Prepare batch writes to reset all daily usage counters
        const batch = firestore.batch();
        let userCount = 0;
        
        usageDocs.forEach((doc) => {
          const userId = doc.id;
          const dailyRef = firestore
              .collection("token_usage")
              .doc(userId)
              .collection("daily")
              .doc(today);
              
          batch.set(dailyRef, {
            tokens_used: 0,
            date: today,
            created_at: admin.firestore.FieldValue.serverTimestamp(),
            last_updated: admin.firestore.FieldValue.serverTimestamp(),
            reset_by: "scheduled-function",
          });
          
          userCount++;
        });
        
        // Execute batch write
        await batch.commit();
        
        // Log success
        console.log(`Successfully reset token usage for ${userCount} users on ${today}`);
        return null;
      } catch (error) {
        console.error("Error in scheduled token usage reset:", error);
        return null;
      }
    });

/**
 * Function to handle webhook events from Stripe
 */
export const stripeWebhook = functions.https.onRequest(
    async (request, response) => {
      try {
        const stripe = require("stripe")(functions.config().stripe.secret_key);
        const signature = request.headers["stripe-signature"];
        const webhookSecret = functions.config().stripe.webhook_secret;
        
        // Verify webhook signature
        let event;
        try {
          event = stripe.webhooks.constructEvent(
              request.rawBody,
              signature,
              webhookSecret
          );
        } catch (err) {
          console.error("Webhook signature verification failed:", err.message);
          response.status(400).send(`Webhook Error: ${err.message}`);
          return;
        }
        
        // Handle the event based on its type
        switch (event.type) {
          case "checkout.session.completed": {
            const session = event.data.object;
            const customerId = session.customer;
            const subscriptionId = session.subscription;
            
            // Find the user with this customer ID
            const usersSnapshot = await firestore
                .collection("users")
                .where("stripe_customer_id", "==", customerId)
                .get();
            
            if (!usersSnapshot.empty) {
              const userDoc = usersSnapshot.docs[0];
              const userId = userDoc.id;
              
              // Update user with subscription details
              await firestore.collection("users").doc(userId).update({
                plan: "premium",
                stripe_subscription_id: subscriptionId,
                subscription_status: "active",
                subscription_updated_at: admin.firestore.FieldValue.serverTimestamp(),
              });
              
              console.log(`User ${userId} successfully subscribed with ID: ${subscriptionId}`);
            } else {
              console.error(`No user found with customer ID: ${customerId}`);
            }
            break;
          }
          
          case "customer.subscription.updated": {
            const subscription = event.data.object;
            const customerId = subscription.customer;
            const status = subscription.status;
            
            // Find the user with this customer ID
            const usersSnapshot = await firestore
                .collection("users")
                .where("stripe_customer_id", "==", customerId)
                .get();
            
            if (!usersSnapshot.empty) {
              const userDoc = usersSnapshot.docs[0];
              const userId = userDoc.id;
              
              // Prepare update data
              const updateData: any = {
                subscription_status: status,
                subscription_updated_at: admin.firestore.FieldValue.serverTimestamp(),
              };
              
              // If active, set to premium plan, otherwise set to free
              if (status === "active") {
                updateData.plan = "premium";
              } else {
                updateData.plan = "free";
              }
              
              // Update user subscription status
              await firestore.collection("users").doc(userId).update(updateData);
              
              console.log(`User ${userId} subscription updated to: ${status}`);
            }
            break;
          }
          
          case "customer.subscription.deleted": {
            const subscription = event.data.object;
            const customerId = subscription.customer;
            
            // Find the user with this customer ID
            const usersSnapshot = await firestore
                .collection("users")
                .where("stripe_customer_id", "==", customerId)
                .get();
            
            if (!usersSnapshot.empty) {
              const userDoc = usersSnapshot.docs[0];
              const userId = userDoc.id;
              
              // Downgrade to free plan
              await firestore.collection("users").doc(userId).update({
                plan: "free",
                subscription_status: "canceled",
                subscription_updated_at: admin.firestore.FieldValue.serverTimestamp(),
              });
              
              console.log(`User ${userId} subscription canceled`);
            }
            break;
          }
          
          default:
            // Unexpected event type
            console.log(`Unhandled event type: ${event.type}`);
        }
        
        // Return a success response
        response.json({received: true});
      } catch (error) {
        console.error("Error processing webhook:", error);
        response.status(500).send(`Webhook Error: ${error.message}`);
      }
    });

/**
 * Function to initialize a new month's usage tracking
 * Runs on the 1st of each month at midnight UTC (cron syntax: 0 0 1 * *)
 */
export const initializeMonthlyUsage = functions.pubsub
    .schedule("0 0 1 * *")
    .timeZone("UTC")
    .onRun(async (context) => {
      try {
        // Get current month in YYYY-MM format
        const date = new Date();
        const year = date.getUTCFullYear();
        const month = (date.getUTCMonth() + 1).toString().padStart(2, "0");
        const currentMonth = `${year}-${month}`;
        
        // Create a new monthly usage document with zero usage
        await firestore.collection("token_usage_monthly").doc(currentMonth).set({
          tokens_used: 0,
          month: currentMonth,
          created_at: admin.firestore.FieldValue.serverTimestamp(),
          last_updated: admin.firestore.FieldValue.serverTimestamp(),
          budget_limit: 2000000, // 2 million tokens monthly budget
        });
        
        console.log(`Initialized token usage for new month: ${currentMonth}`);
        return null;
      } catch (error) {
        console.error("Error initializing monthly usage:", error);
        return null;
      }
    });
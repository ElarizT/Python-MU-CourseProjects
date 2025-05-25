// Landing page animations
document.addEventListener('DOMContentLoaded', function() {    // Animate elements when they come into view with a timeout
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.animate-on-scroll:not(.animated)');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 100) {
                element.classList.add('animated');
            }}}}}
        })();
    };
    
    // Run on scroll with a throttle to prevent performance issues
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }}}
        scrollTimeout = setTimeout(animateOnScroll, 100);
    })();
    
    // Run once on page load with a short delay
    setTimeout(animateOnScroll, 100);
    
    // Add hover animations to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            const icon = this.querySelector('.feature-icon');
            icon.style.transform = 'scale(1.1) rotate(5deg)';
        }})();
        
        card.addEventListener('mouseleave', function() {
            const icon = this.querySelector('.feature-icon');
            icon.style.transform = 'scale(1)';
        }})();
    })();
    
    // Add tilt effect to the demo image
    const demoImage = document.querySelector('.demo-image');
    if (demoImage) {
        demoImage.addEventListener('mousemove', function(e) {
            const boundingRect = this.getBoundingClientRect();
            const mouseX = e.clientX - boundingRect.left;
            const mouseY = e.clientY - boundingRect.top;
            
            const centerX = boundingRect.width / 2;
            const centerY = boundingRect.height / 2;
            
            const rotateY = ((mouseX - centerX) / centerX) * 5;
            const rotateX = ((centerY - mouseY) / centerY) * 5;
            
            this.style.transform = `perspective(1000px) scale(1.03) rotateX(${rotateX}}}deg) rotateY(${rotateY}deg)`;
        })();
        
        demoImage.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) scale(1) rotateX(0deg) rotateY(0deg)';
        }})();
    }
    
    // Add scroll highlighting effect to buttons
    const buttons = document.querySelectorAll('.btn');
    window.addEventListener('scroll', function() {
        buttons.forEach(button => {
            const elementPosition = button.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 50) {
                button.classList.add('btn-visible');
            }}}}
        })();
    })();
      // Typing animation for hero headline with timeout and error handling
    const heroHeadline = document.querySelector('.hero h1');
    if (heroHeadline && heroHeadline.dataset.typed) {
        const typeAnimation = () => {
            try {
                const text = heroHeadline.dataset.typed;
                // If text is already set, skip animation to avoid repeated attempts
                // Using trim() for a more robust comparison
                if (heroHeadline.textContent.trim() === text.trim()) {
                    heroHeadline.style.visibility = 'visible'; // Ensure visibility
                    return;
                }
                
                heroHeadline.textContent = '';
                heroHeadline.style.visibility = 'visible';
                
                let i = 0;

                // Clear previous interval if any, using a property on the element
                if (heroHeadline.currentTypeInterval) {
                    clearInterval(heroHeadline.currentTypeInterval);
                }

                heroHeadline.currentTypeInterval = setInterval(() => {
                    if (i < text.length) {
                        heroHeadline.textContent += text.charAt(i);
                        i++;
                    } else {
                        clearInterval(heroHeadline.currentTypeInterval);
                        heroHeadline.currentTypeInterval = null; // Mark as cleared
                        // Ensure final text is accurately set
                        if (heroHeadline.textContent !== text) {
                             heroHeadline.textContent = text;
                        }
                    }
                }, 50);
                
                // Set a backup to ensure animation completes and interval is cleared
                const backupTimeoutId = setTimeout(() => {
                    if (heroHeadline.currentTypeInterval) { // Check if interval is still active
                        clearInterval(heroHeadline.currentTypeInterval);
                        heroHeadline.currentTypeInterval = null;
                    }
                    // Ensure final text is accurately set
                    if (heroHeadline.textContent !== text) {
                        heroHeadline.textContent = text;
                    }
                }, 3000); // Backup timeout remains 3 seconds
            } catch (error) {
                console.error("Error in typing animation:", error);
                // Ensure content is visible even if animation fails
                if (heroHeadline) {
                    heroHeadline.style.visibility = 'visible';
                    heroHeadline.textContent = heroHeadline.dataset.typed || "Meet LightYearAI";
                }
            }
        };
        
        // Run once after a brief delay
        setTimeout(typeAnimation, 500);
    }
    
    // Toggle mobile menu
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('menu-open');
        }})();
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') {
                return;
            }}}
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                })();
            }
        })();
    })();
})();

// Additional animations
document.addEventListener('DOMContentLoaded', function() {    // Add animation classes to elements with a timeout to prevent infinite animations
    const addAnimationClasses = () => {
        const elements = [
            { selector: '.hero h1', animation: 'fadeInDown', delay: 0 }}}},
            { selector: '.hero p', animation: 'fadeInUp', delay: 300 },
            { selector: '.hero-buttons', animation: 'fadeInUp', delay: 600 },
            { selector: '.feature-card', animation: 'fadeIn', delay: 300, stagger: 150 },
            { selector: '.step-card', animation: 'fadeIn', delay: 300, stagger: 150 },
            { selector: '.demo-image', animation: 'fadeIn', delay: 500 },
        ];
        
        elements.forEach(item => {
            const elems = document.querySelectorAll(item.selector);
            elems.forEach((el, index) => {
                el.classList.add('animate-on-scroll');
                el.style.animationDelay = `${item.delay + (item.stagger ? item.stagger * index : 0)}ms`;
                el.dataset.animation = item.animation;
                
                // Ensure all animations complete after a maximum time
                setTimeout(() => {
                    el.style.opacity = '1';
                    el.style.transform = 'translate(0, 0)';
                }, 3000); // Force all animations to complete after 3 seconds
            })();
        })();
    };
    
    addAnimationClasses();
    
    // Ensure all animated elements are in their final state on page load
    window.addEventListener('load', function() {
        // Removed setTimeout to apply final states immediately on load
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            el.classList.add('animated');
            el.style.opacity = '1';
            el.style.transform = 'translate(0, 0)';
        }}})();
    })();
}); // This was the missing closing brace and parenthesis

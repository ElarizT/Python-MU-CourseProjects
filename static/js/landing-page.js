// Landing page animations
document.addEventListener('DOMContentLoaded', function() {
    // Animate elements when they come into view
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.animate-on-scroll');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 100) {
                element.classList.add('animated');
            }
        });
    };
    
    // Run on scroll
    window.addEventListener('scroll', animateOnScroll);
    // Run once on page load
    setTimeout(animateOnScroll, 100);
    
    // Add hover animations to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            const icon = this.querySelector('.feature-icon');
            icon.style.transform = 'scale(1.1) rotate(5deg)';
        });
        
        card.addEventListener('mouseleave', function() {
            const icon = this.querySelector('.feature-icon');
            icon.style.transform = 'scale(1)';
        });
    });
    
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
            
            this.style.transform = `perspective(1000px) scale(1.03) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
        
        demoImage.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) scale(1) rotateX(0deg) rotateY(0deg)';
        });
    }
    
    // Add scroll highlighting effect to buttons
    const buttons = document.querySelectorAll('.btn');
    window.addEventListener('scroll', function() {
        buttons.forEach(button => {
            const elementPosition = button.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 50) {
                button.classList.add('btn-visible');
            }
        });
    });
    
    // Typing animation for hero headline
    const heroHeadline = document.querySelector('.hero h1');
    if (heroHeadline && heroHeadline.dataset.typed) {
        const typeAnimation = () => {
            const text = heroHeadline.dataset.typed;
            heroHeadline.textContent = '';
            heroHeadline.style.visibility = 'visible';
            
            let i = 0;
            const typeInterval = setInterval(() => {
                if (i < text.length) {
                    heroHeadline.textContent += text.charAt(i);
                    i++;
                } else {
                    clearInterval(typeInterval);
                }
            }, 50);
        };
        
        setTimeout(typeAnimation, 500);
    }
    
    // Toggle mobile menu
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('menu-open');
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
});

// Additional animations
document.addEventListener('DOMContentLoaded', function() {
    // Add animation classes to elements
    const addAnimationClasses = () => {
        const elements = [
            { selector: '.hero h1', animation: 'fadeInDown', delay: 0 },
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
            });
        });
    };
    
    addAnimationClasses();
});

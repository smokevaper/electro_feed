<div class="admin-actions">
    <a href="{{ url_for('add_product') }}" class="admin-btn primary">
        <i class="fas fa-plus"></i> Добавить товар
    </a>
    <a href="{{ url_for('manage_categories') }}" class="admin-btn secondary">
        <i class="fas fa-tags"></i> Управление категориями
    </a>
</div>
document.addEventListener('DOMContentLoaded', function() {
    // Navigation functionality
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section');
    
    // Smooth scrolling for navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Category filter functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    const allProducts = document.querySelectorAll('.product-card');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active filter button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            const category = this.getAttribute('data-category');
            console.log('Selected category:', category);
            
            // Filter products
            allProducts.forEach(product => {
                const productCategory = product.getAttribute('data-category');
                if (category === 'all' || productCategory === category) {
                    product.style.display = 'block';
                    // Add animation
                    product.style.opacity = '0';
                    product.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        product.style.opacity = '1';
                        product.style.transform = 'translateY(0)';
                    }, 100);
                } else {
                    product.style.display = 'none';
                }
            });
        });
    });
    
    // Header scroll effect
    const header = document.querySelector('.header');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            header.style.background = 'rgba(0, 0, 0, 0.98)';
        } else {
            header.style.background = 'rgba(0, 0, 0, 0.95)';
        }
    });
    
    // Intersection Observer for section highlighting
    const observerOptions = {
        threshold: 0.6,
        rootMargin: '-100px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const sectionId = entry.target.id;
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, observerOptions);
    
    sections.forEach(section => {
        observer.observe(section);
    });
    
    // Add animation effects for product cards
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.product-card, .contact-item, .certificate');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    };
    
    // Initialize elements for animation
    const elements = document.querySelectorAll('.product-card, .contact-item, .certificate');
    elements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });
    
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Run once on load
    
    // Add product hover effects
    const productCards = document.querySelectorAll('.product-card');
    productCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
            this.style.boxShadow = '0 20px 40px rgba(139, 92, 246, 0.3)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.boxShadow = '0 10px 30px rgba(139, 92, 246, 0.2)';
        });
    });
});

// Add interactive effects for buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('cta-button') || e.target.classList.contains('filter-btn')) {
        // Create ripple effect
        const ripple = document.createElement('span');
        const rect = e.target.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        e.target.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
});

// Add CSS for ripple effect and animations
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .cta-button, .filter-btn {
        position: relative;
        overflow: hidden;
    }
    
    .product-card {
        transition: all 0.3s ease;
    }
    
    .product-image {
        transition: transform 0.3s ease;
    }
    
    .product-card:hover .product-image {
        transform: scale(1.1) rotate(5deg);
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(139, 92, 246, 0); }
        100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
    }
    
    .price-notice {
        animation: pulse 2s infinite;
    }
`;
document.head.appendChild(style);

// Add price converter tooltip (placeholder for future functionality)
document.querySelectorAll('.price').forEach(priceElement => {
    priceElement.addEventListener('click', function() {
        alert('Для получения точной стоимости в рублях обратитесь к менеджеру в Telegram: @vape_feed_original');
    });
});

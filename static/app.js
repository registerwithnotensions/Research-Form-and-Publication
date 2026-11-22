document.addEventListener("DOMContentLoaded", () => {

    // Smooth navigation
    document.querySelectorAll('nav a').forEach(link => {

        link.addEventListener("click", function(event) {

            const target = document.querySelector(
                this.getAttribute("href")
            );

            if (target) {
                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth"
                });
            }

        });

    });


    // Research form confirmation
    const form = document.querySelector(".research-form");

    if (form) {

        form.addEventListener("submit", function() {

            const button = form.querySelector("button");

            button.textContent = "Publishing...";
            button.disabled = true;

        });

    }

});

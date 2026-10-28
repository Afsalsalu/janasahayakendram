document.getElementById('searchBar').addEventListener('input', function () {
    const query = this.value.toLowerCase();
    const services = document.querySelectorAll('.service-card');

    services.forEach(service => {
        const serviceName = service.querySelector('h5').textContent.toLowerCase();
        if (serviceName.includes(query)) {
            service.style.display = 'block';
        } else {
            service.style.display = 'none';
        }
    });
});
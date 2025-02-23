// Validate the form fields before submission
function validateForm(event) {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();

    if (email === '' || password === '') {
        alert('Please fill in all fields.');
        event.preventDefault();
        return false;
    }

    if (!validateEmail(email)) {
        alert('Please enter a valid email address.');
        event.preventDefault();
        return false;
    }

    return true;
}

function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

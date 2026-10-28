const button = document.getElementById('dynamicButton');

// Add hover effect using JavaScript
button.addEventListener('mouseover', function() {
    button.style.backgroundColor = 'yellow';
});

button.addEventListener('mouseout', function() {
    button.style.backgroundColor = 'lightgray';
});

// Add click effect using JavaScript
button.addEventListener('mousedown', function() {
    button.style.backgroundColor = 'black';
    button.style.color = 'white';
});

// Revert to default state when mouse is released
button.addEventListener('mouseup', function() {
    button.style.backgroundColor = 'lightgray';
    button.style.color = 'black';
});



// Function to close the popup when the user clicks "OK"
function closePopup() {
    document.getElementById("popup").style.display = "none";
    document.getElementById("overlay").style.display = "none";
}

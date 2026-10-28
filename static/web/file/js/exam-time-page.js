<script>
    var initialDiv = document.getElementById('initialDiv');
    var examForm = document.getElementById('examForm');
    var timerDisplay = document.getElementById('timer');
    var examFormElement = document.getElementById('examFormElement');
    var timeLeft = 600; // 10 minutes in seconds
    var timerInterval;
    var assessmentsUrl = "{% url 'exam:assessments' %}";

        function startExam(event) {
        event.preventDefault();  // Prevent form submission
        console.log("Exam started");  // Debugging line
        initialDiv.style.display = 'none';
        examForm.style.display = 'block';
        timerInterval = setInterval(updateTimer, 1000);
        
        // Request full screen mode
        requestFullScreen(document.documentElement);
    }
    


    function requestFullScreen(element) {
        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.webkitRequestFullscreen) { // Safari
            element.webkitRequestFullscreen();
        } else if (element.msRequestFullscreen) { // IE/Edge
            element.msRequestFullscreen();
        }
    }

    function exitFullScreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) { // Safari
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) { // IE/Edge
            document.msExitFullscreen();
        }
    }

    function updateTimer() {
        var minutes = Math.floor(timeLeft / 60);
        var seconds = timeLeft % 60;

        // Display the remaining time in MM:SS format
        timerDisplay.textContent = (minutes < 10 ? '0' : '') + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            timerDisplay.textContent = '00:00';
            // Hide the form and redirect to home page after 10 minutes
            examForm.style.display = 'none';
            alert('Exam time is over. You will be redirected to the home page.');
            window.location.href = assessmentsUrl;
            exitFullScreen();
        } else {
            timeLeft--; // Decrease time left by 1 second
        }
    }

    examFormElement.addEventListener('submit', function (event) {
        clearInterval(timerInterval); // Stop the timer
        // Proceed with the form submission
    });

    // Detect if the tab is hidden or visible
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') {
            alert('You left the exam. You will be redirected to the home page.');
            exitFullScreen();
            window.location.href = assessmentsUrl;
        }
    });

    // Detect changes in full-screen mode
    document.addEventListener('fullscreenchange', function () {
        if (!document.fullscreenElement) {
            alert('You exited full-screen mode. You will be redirected to the home page.');
            window.location.href = assessmentsUrl;
        }
    });
    document.addEventListener('webkitfullscreenchange', function () {
        if (!document.webkitFullscreenElement) {
            alert('You exited full-screen mode. You will be redirected to the home page.');
            window.location.href = assessmentsUrl;
        }
    });
    document.addEventListener('mozfullscreenchange', function () {
        if (!document.mozFullScreenElement) {
            alert('You exited full-screen mode. You will be redirected to the home page.');
            window.location.href = assessmentsUrl;
        }
    });
    document.addEventListener('msfullscreenchange', function () {
        if (!document.msFullscreenElement) {
            alert('You exited full-screen mode. You will be redirected to the home page.');
            window.location.href = assessmentsUrl;
        }
    });

    document.addEventListener('DOMContentLoaded', function () {
    var startButton = document.getElementById('startButton');
    if (startButton) {
        console.log("Button found");  // Debugging log
        startButton.addEventListener('click', function() {
            console.log("Start Exam button clicked!");
            startExam();  // Call the startExam function
        });
    } else {
        console.error("Button not found");
    }
});

</script>
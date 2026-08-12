<?php 

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Sanitize and validate input data
    $name = filter_var($_POST['name'], FILTER_SANITIZE_STRING);
    $email = filter_var($_POST['email'], FILTER_SANITIZE_EMAIL);
    $message = filter_var($_POST['message'], FILTER_SANITIZE_STRING);

    $output = "<pre>
    ---
    user:
      name: $name
      email: $email
      message: $message
    ---
        </pre>";

    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        loadContent('body', '<div class="alert-error">Invalid email format.</div>');
        exit;
    }

  // Here you would typically send the email or store the message in a database
  // For this example, we'll just display a success message
  loadContent('body', '<div class="alert-success">Thank you for your message, ' . htmlspecialchars($name) . '! We will get back to you at ' . htmlspecialchars($email) . '</div>');
  loadContent('body', $output);
} else {
  loadContent('body', '<div class="alert-error">Invalid request method.</div>');
}

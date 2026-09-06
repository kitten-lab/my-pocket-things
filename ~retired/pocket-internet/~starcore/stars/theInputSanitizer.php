<?php
function inputSanitizer(string $data) {
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data);
    return $data;
} 

function wirePostInput(string $name) {
    return isset($_POST[$name]) ? inputSanitizer($_POST[$name]) : '';
}
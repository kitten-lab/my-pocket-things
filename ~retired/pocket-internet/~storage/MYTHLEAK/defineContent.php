<?php
include_once(__DIR__ . '/house/navigation.php');
include_once(__DIR__ . '/house/header.php');
include_once(__DIR__ . '/house/footer.php');

loadContent('styles', "<meta name='viewport' content='width=device-width, initial-scale=1'>");

$key = keyMaker('home');
lockAndKey($key);

<?php
/** CHESTER'S NOTE: This file defines the content for different sections of the page. 
 * This is just a working example of a content fill. */
include_once(__DIR__ . '/navigation.php');
include_once(__DIR__ . '/header.php');
include_once(__DIR__ . '/footer.php');

$key = keyMaker('home');
lockAndKey($key);
?>
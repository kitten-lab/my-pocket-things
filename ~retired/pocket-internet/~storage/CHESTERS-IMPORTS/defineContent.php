<?php
/** CHESTER'S NOTE: This file defines the content for different sections of the page. 
 * This is just a working example of a content fill. */

// local area definitions for this space
define('SHOP_DOOR', URL_ROOT . '/~server' . Space_URI);

include_once(__DIR__ . '/house/navigation.php');
include_once(__DIR__ . '/house/header.php');
include_once(__DIR__ . '/house/footer.php');

loadContent('styles', "<meta name='viewport' content='width=device-width, initial-scale=1'>");

$key = keyMaker('home');
lockAndKey($key);
?>

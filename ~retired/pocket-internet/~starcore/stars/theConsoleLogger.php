<?php
/** CHESTER'S NOTE: This function logs messages to the console with different colors based on the message type. */

function consoleLogger(string $output, ?string $type = "INFO") {
  if ($type == "ERROR") {
    $CSS_insert = "color: red";
  } elseif ($type == "SUCCESS") {
    $CSS_insert = "color: green";
  } elseif ($type == "BOOT_MSG"){
    $CSS_insert = "color: black; font-size: 13px; font-family: monospace;";
  } else {
    $CSS_insert = "color: gray";
  }
    loadContent('logs', '<script>console.log("%c' . $type . ': ' . $output . '", "' . $CSS_insert . '");</script>');
}

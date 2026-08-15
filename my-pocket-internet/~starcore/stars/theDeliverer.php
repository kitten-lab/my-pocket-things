<?php
/** CHESTER'S NOTE: TheDeliverer is responsible for delivering content to the appropriate locations within myPI.
 * It provides functions to set drop spots, load content, and manage the delivery of content to specific locations
 * on the shell. */

/** setDropSpot function is responsible for placing drop locations on the shells for content delivery. */
function setDropSpot(string $dropSpot) {
  consoleLogger("loading content for drop spot: " . $dropSpot);
  if (!empty($GLOBALS['DropSpot'][$dropSpot])) {
    foreach ($GLOBALS['DropSpot'][$dropSpot] as $fn) {
      echo $fn();
    }
    consoleLogger("loaded " . $dropSpot, "SUCCESS");
  } else {
    consoleLogger("NO CONTENT FOUND " . $dropSpot, "ERROR");
  }
}

/** loadContent function is responsible for loading content into a specific drop spot. */
function loadContent(string $location, string $result) {
  setDelivery($location, $result);
}

/** setDelivery function is responsible for storing and delivering the content for each drop spot. */
function setDelivery(string $location, string $payload) {
  $GLOBALS['DropSpot'][$location][] = function () use ($payload) {
    return $payload;
  };
}

/** Queue a PHP file to run when that drop fires. Echo nothing (include's 1 stays off the page). */
function loadRun(string $location, string $file): void {
  $GLOBALS['DropSpot'][$location][] = function () use ($file) {
    include $file;
    return '';
  };
}
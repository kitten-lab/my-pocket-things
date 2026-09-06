<?php
/** CHESTER'S NOTE: The door opener for the starry night. When you need a room
 * The keyMaker function generates a key based on the requested page, and the lockAndKey function 
 * checks if the corresponding room file exists. If it does, it loads the room; if not, it logs an error 
 * and displays a message to the user.
 */

function keyMaker(?string $default = 'home'): string {
  $raw = $_GET['key'] ?? $default;
  // only a plain name — no paths, no ..
  $key = strtolower(preg_replace('/[^a-z0-9_-]/i', '', (string) $raw));
  return $key !== '' ? $key : $default;
}

function lockAndKey(string $key): void {
  $path = STORAGE_ROOT . '/' . Space_Slug . '/rooms/' . $key . '.php';
  if (!is_file($path)) {
    consoleLogger("No key found: {$key}", 'ERROR');
    loadContent('body', '<p>No key found. Tell MOM.</p>');
    return;
  }
  consoleLogger("unlocked room: {$key}", 'SUCCESS');
  require $path; // room only loadContent's into spots
}
<?php
/** CHESTER'S NOTE: A tool is a folder. Parts are files in it.
 * loadTool('contact') seats every part. loadTool('viewer/box') seats one. */

function loadTool(string $tool): void {
  $root = PI_ROOT . '/~starstore/tools/';
  $files = [];

  if (strpos($tool, '/') !== false) {
    [$folder, $part] = explode('/', $tool, 2);
    $path = $root . $folder . '/' . $part . '.php';
    if (is_file($path)) {
      $files[$path] = $part;
    }
  } else {
    $dir = $root . $tool;
    foreach (glob($dir . '/*.php') ?: [] as $path) {
      $files[$path] = basename($path, '.php');
    }
  }

  if ($files === []) {
    consoleLogger('loadTool found no parts for ' . $tool, 'ERROR');
    return;
  }

  foreach ($files as $path => $part) {
    if ($part === 'act') {
      loadRun('server', $path);
      continue;
    }

    ob_start();
    $returned = include $path;
    $sprayed = ob_get_clean();
    if (is_string($returned) && $returned !== '') {
      loadContent('body', $returned);
    } elseif (is_string($sprayed) && $sprayed !== '') {
      loadContent('body', $sprayed);
    }
  }
}

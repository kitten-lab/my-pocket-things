<?php
/** CHESTER'S NOTE: This file defines the paths for the project. 
 * It sets the root paths for the project, starcore, storage, shells, and styles. 
 * It also defines the URL root for the project. */

if (!defined('PI_ROOT')) {
  define('PI_ROOT', realpath(__DIR__ . '/..'));
}

if (ENVIRONMENT === 'rosewood') {
  define('URL_ROOT', 'http://go.alice');
} else {
  define('URL_ROOT', 'http://be.imported.to/');
}

define('STARCORE_ROOT', realpath(PI_ROOT . '/~starcore'));
define('STORAGE_ROOT', realpath(PI_ROOT . '/~storage'));
define('SHELLS_ROOT', realpath(PI_ROOT . '/~shells'));
define('STYLES_ROOT', realpath(PI_ROOT . '/~styles'));

define('ALICE_STYLES',  URL_ROOT . '/~styles');

?>
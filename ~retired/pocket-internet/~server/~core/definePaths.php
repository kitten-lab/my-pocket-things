<?php
/** CHESTER'S NOTE: This file defines the paths for the project. 
 * It sets the root paths for the project, starcore, storage, shells, and styles. 
 * It also defines the URL root for the project. */

// unused fallback, for potential later use
if (!defined('PI_ROOT')) {
  define('PI_ROOT', realpath(__DIR__ . '/..'));
}

// declare URL_ROOT based on the environment
if (ENVIRONMENT === 'rosewood') {
  define('URL_ROOT', 'http://go.alice');
} else {
  define('URL_ROOT', 'http://be.imported.to/');
}

// simple path definitions
define('STARCORE_ROOT', realpath(PI_ROOT . '/~starcore'));
define('STORAGE_ROOT', realpath(PI_ROOT . '/~storage'));
define('SHELLS_ROOT', realpath(PI_ROOT . '/~shells'));
define('STYLES_ROOT', realpath(PI_ROOT . '/~styles/forShells'));
define('MASTERSTORE_ROOT', realpath(STORAGE_ROOT . '/~library/chips'));
define('MASTERGOODS_ROOT', STORAGE_ROOT . '/~library/goods');
define('MASTERKINDS_ROOT', STORAGE_ROOT . '/~library/kinds');

// requiring URL_ROOT definitions
define('SPACES_ROOT', URL_ROOT . '/~server/' . Space_URI . '/');
define('ALICE_STYLES',  URL_ROOT . '/~styles/forShells');
define('DRESS_ROOT', URL_ROOT . '/~storage/' . Space_URI . '/house/dress/');

?>
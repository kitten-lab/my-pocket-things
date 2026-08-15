<?php
/** MYTHLEAK — enter the leak. Same shell. Different dress. */

require_once(__DIR__ . '/defineSpace.php');
require_once(PI_ROOT . '/~starcore/establishEnvo.php');
require_once(PI_ROOT . '/~server/~core/definePaths.php');
require_once(STARCORE_ROOT . '/invokeCore.php');

consoleLogger('ENVIRONMENT: ' . ENVIRONMENT, 'BOOT_MSG');
consoleLogger(Space_Slug . ' by ' . Space_Author . " > " . Space_Description, "BOOT_MSG");
include_once(STORAGE_ROOT . '/' . Space_Slug . '/defineContent.php');

// leak + press = standard article dress. leak + mythleak = the RGB site.
generateShell('leak', 'mythleak');

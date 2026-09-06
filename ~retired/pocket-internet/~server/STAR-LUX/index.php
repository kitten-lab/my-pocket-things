<?php
/** CHESTER'S NOTE: This is the main entry point for the space. 
 * It loads the necessary definitions, invokes the starcore, and generates the shell for rendering. */

// load the space definitions, path definitions
require_once(__DIR__ . '/defineSpace.php');

// load the environment definitions, path definitions
require_once(PI_ROOT . '/~starcore/establishEnvo.php');
require_once(PI_ROOT . '/~server/~core/definePaths.php');

// load the DSL starcore
require_once(STARCORE_ROOT . '/invokeCore.php');

// load the content for the space and announce the space to the console
consoleLogger('ENVIRONMENT: ' . ENVIRONMENT, 'BOOT_MSG');
consoleLogger(Space_Slug . ' by ' . Space_Author . " > " . Space_Description, "BOOT_MSG");
require_once(STORAGE_ROOT . '/' . Space_Slug . '/defineContent.php');

// generate the shell for rendering the space
generateShell('simple', 'space-manager');

?>



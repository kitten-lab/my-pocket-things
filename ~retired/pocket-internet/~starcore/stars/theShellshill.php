<?php
/** CHESTER'S NOTE: This function is used to load a shell and its corresponding style. 
 * It checks if the shell file exists, and if not, it loads a default shell. 
 * It also checks if the style file exists, and if not, it loads a default style. 
 * The function logs messages to the console for debugging purposes. */

function generateShell(string $shellClass, string $styleClass) {

  if (!is_file(SHELLS_ROOT . '/' . $shellClass . '.php')) {

    consoleLogger("Cannot find your Shell! Loading replacement (default). Missing: "
    . $shellClass . ".php", "ERROR");
    
    if (!is_file(STYLES_ROOT . '/' . $shellClass . '/' . $styleClass . '.css')) {
      loadContent('styles', "<link rel='stylesheet' href='" 
      . ALICE_STYLES . "/default/default.css'>");

      consoleLogger('Cannot find your Style! Loading replacement (default/default.css). Missing: ' 
      . $styleClass . ".css", "ERROR"); 

    } else {
      loadContent('styles', "<link rel='stylesheet' href='" 
      . ALICE_STYLES . "/" 
      . $shellClass . "/" 
      . $styleClass . ".css'>");
      consoleLogger('loaded style: ' . $styleClass . ".css", "SUCCESS"); 
    }

    require_once(SHELLS_ROOT . '/default.php');
    return;
  
    } else {

      if (!is_file(STYLES_ROOT . '/' . $shellClass . '/' . $styleClass . '.css')) {
        loadContent('styles', "<link rel='stylesheet' href='" 
        . ALICE_STYLES . "/default/default.css'>");

        consoleLogger('Cannot find your Style! Loading replacement (default/default.css). Missing: ' 
         . $styleClass . ".css", "ERROR"); 

      } else {
        loadContent('styles', "<link rel='stylesheet' href='" 
        . ALICE_STYLES . "/" 
        . $shellClass . "/" 
        . $styleClass . ".css'>");

        consoleLogger('loaded style: ' . $styleClass . ".css", "SUCCESS"); 
      }

    consoleLogger('loaded shell: ' . $shellClass . ".php", "SUCCESS");
    require_once(SHELLS_ROOT . '/' . $shellClass . '.php');
  }
}
?>  
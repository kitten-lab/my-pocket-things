---
store:
  file: leaf[4]-composablecodebase.chip
chip:
  uid: leaf[4]
  name: composable code base
  auth: AUORI
pin:
  tps_created: 1785941319
  tps_updated: 1785964257
  tags: []
---
# Composable Code Base

The entirety of [[POCKET OS]] must run on a clean and almost hallow core, with only the required runtimes needed to launch the environment. Even in this case, all functions should be stored and managed as separated parts. Future product should allow a core functionality to be re-written by a creator in the community and offered as a replacement to even the most fundamental core functionalities of [[POCKET OS]] and its platform core.

### CASE STUDY (not final code or folder structure, for example only)
> launch process calls required materials
```
  require_once echoSONAR . '/Dialects/myJacks.lang.php';
  require_once echoSONAR . '/Definitions/root.def.php';
  require_once echoSONAR . '/Dialects/chestersImports.lang.php';
  require_once echoSONAR . '/Dialects/wireWolf.lang.php';
  require_once echoSONAR . '/Dialects/skySongs.lang.php';
```
> each material called, calls its parts
```
function callWolves(){
  return [
  [ "caller" => "fetch", "class" => "pup" ],
  [ "caller" => "db", "class" => "pup" ],
  [ "caller" => "aleph", "class" => "ox" ],
  [ "caller" => "wireInput", "class" => "form" ],
  [ "caller" => "wireTextarea", "class" => "form" ],
  [ "caller" => "wireButton", "class" => "form" ],

  ];
}

$WOLVES = callWolves();

jackReport("CALLING ALL WOLVES","background-color:black;color:white;padding:20px;");

foreach ($WOLVES as $Wolfie) {
  $echoLocate = __DIR__ . '/wireWolf/' . $Wolfie['caller'] . "." . $Wolfie['class'] . ".php";
  if (!file_exists($echoLocate)){
    $missingWolfes[] = $Wolfie['caller'];
  } else {
    include $echoLocate;
    $foundWolves[] = $Wolfie['caller'];
  }
}

if(!empty($foundWolves)){
  $confirm_message = "You howl at the moon. The wolves respond by drawing near. " 
  . count($foundWolves) . " of " . count($WOLVES) . " wolves approach with glowing eyes: " 
  . implode(", ", $foundWolves);
  jackReport($confirm_message);
}

if (!empty($missingWolfes)){
  $fail_message = count($missingWolfes) 
  . " Missing Wolves. Alert the pack lead, the following are missing: " . implode(", ", $missingWolfes);
  jackReportError("!!! LANGUAGE IMPORT ERROR, PLEASE REPORT!!! MISSING", $fail_message);
}
```
> each function is contained within its own code
```
function getTool($tool, $function) {
  $GLOBALS['JX']['sets'][] = function() use ($tool, $function) { 
    getToolNIM($tool, 'set', $function);
    };
  $GLOBALS['JX']['acts'][] = function() use ($tool, $function) {
    getToolNIM($tool, 'act', $function);
    };
  $GLOBALS['JX']['kits'][] = function() use ($tool, $function) {
    getToolNIM($tool, 'kit', $function);

    };
}

function loadTool($tool, $type, $function) {
  $result = ROUTE_TO_ROMS . $tool . "/" . $function . "." . $type . ".php";
    if (is_file($result)) {
    include $result;
    } else {
       jackReportWarn("KDE! Tool file not found. " . $result);
    }  
  }
```

Only the parts required are called, and all parts must be stored as their own pieces which can be called and injected in order, working together or in parts, depending on the surface the core is processing at that time.
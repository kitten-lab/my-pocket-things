<?php
/** CHESTER'S NOTE: A chip is a paper, not a Jason.
 * Two rooms in one file: the head (between the --- lines) and the body (after).
 * Going lower is just walking the names you already wrote: chip, then title.
 * Each dot is one floor down. */

/** Write a chip head + letter. Sections are the frontmatter lines. */
function chipHead(array $tree, string $letter): string {
  $out = "---\n";
  foreach ($tree as $section => $fields) {
    $out .= $section . ":\n";
    foreach ($fields as $name => $value) {
      $out .= "  " . $name . ": " . $value . "\n";
    }
  }
  $out .= "---\n";
  if ($letter !== '') {
    $out .= $letter . "\n";
  }
  return $out;
}

/** Get a specific chip from the query string. */
function fetchChip(string $chipName) {
  if (!isset($_GET['open']) || $_GET['open'] === '') {
    $_GET['open'] = $chipName;
  }
}


/** Split a chip file into head (tree) and body (the letter). */
function openChip(string $path): ?array {
  if (!is_file($path)) {
    consoleLogger("no chip at: " . $path, "ERROR");
    return null;
  }

  $raw = file_get_contents($path);
  if ($raw === false) {
    consoleLogger("could not read chip: " . $path, "ERROR");
    return null;
  }

  $parts = preg_split('/^---\s*$/m', $raw);
  // a written chip looks like: (empty) / head / body
  if (count($parts) < 3) {
    consoleLogger("chip has no head/body gates (---): " . $path, "ERROR");
    return null;
  }

  return [
    'file' => $path,
    'head' => readChipHead($parts[1]),
    'body' => ltrim($parts[2], "\r\n"),
  ];
}

/** Turn the indented head into the same kind of tree Jason would have given you. */
function readChipHead(string $head): array {
  $tree = [];
  $section = null;

  foreach (preg_split("/\r\n|\n|\r/", $head) as $line) {
    if (trim($line) === '') {
      continue;
    }

    $indent = strlen($line) - strlen(ltrim($line, ' '));
    $line = ltrim($line, ' ');
    $cut = strpos($line, ':');
    if ($cut === false) {
      continue;
    }

    $name = trim(substr($line, 0, $cut));
    $value = trim(substr($line, $cut + 1));
    if ($name === '') {
      continue;
    }

    if ($indent === 0) {
      if ($value === '') {
        $section = $name;
        $tree[$section] = [];
      } else {
        $section = null;
        $tree[$name] = readChipValue($value);
      }
      continue;
    }

    if ($section === null) {
      continue;
    }
    $tree[$section][$name] = readChipValue($value);
  }

  return $tree;
}

/** A value is a word, or a little list written [like, this]. */
function readChipValue(string $value) {
  if ($value === '[]') {
    return [];
  }
  if (strlen($value) >= 2 && $value[0] === '[' && substr($value, -1) === ']') {
    $inside = trim(substr($value, 1, -1));
    if ($inside === '') {
      return [];
    }
    $items = [];
    foreach (explode(',', $inside) as $item) {
      $items[] = trim($item);
    }
    return $items;
  }
  return $value;
}

/** Ask the paper a path. 'chip.title' goes into chip, then title. 'body' is the letter. */
function chipAsk(?array $paper, string $path) {
  if ($paper === null) {
    return null;
  }
  if ($path === 'body') {
    return $paper['body'];
  }

  $here = $paper['head'];
  foreach (explode('.', $path) as $floor) {
    if (!is_array($here) || !array_key_exists($floor, $here)) {
      return null;
    }
    $here = $here[$floor];
  }
  return $here;
}

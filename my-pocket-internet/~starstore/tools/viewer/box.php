<?php
/** Chip box — open one local copy and walk downstairs with chipAsk. */

$rawOpen = $_GET['open'] ?? '';
$open = preg_replace('/[^a-zA-Z0-9._-]/', '', (string) $rawOpen);
if ($open === '') {
  return;
}

$dir = dirFinder(Space_Slug, 'library/chips');
$path = $dir . '/' . $open;
$paper = openChip($path);
if ($paper === null) {
  loadContent('body', "<p>Could not open that chip.</p>");
  return;
}

$title = (string) chipAsk($paper, 'chip.title');
$from = chipAsk($paper, 'contact.from');
$mint = chipAsk($paper, 'notch.mint');
$price = chipAsk($paper, 'prop.price') ?? chipAsk($paper, 'listing.price');
$stock = chipAsk($paper, 'prop.stock') ?? chipAsk($paper, 'listing.stock');
$category = chipAsk($paper, 'prop.category') ?? chipAsk($paper, 'listing.category');
$props = chipAsk($paper, 'prop');
$tags = chipAsk($paper, 'notch.tags');
$cites = chipAsk($paper, 'notch.cites');
$letter = (string) chipAsk($paper, 'body');
$dek = chipAsk($paper, 'prop.dek') ?? chipAsk($paper, 'article.dek');
$auth = (string) chipAsk($paper, 'chip.auth');
$writer = ($auth !== '' && $auth !== Space_Slug && $auth !== Space_Author) ? $auth : '';

$html = "<article class='chip-box'>";

if (is_array($cites) && isset($cites[0])) {
  $src = localGoodUrl((string) $cites[0]);
  if ($src) {
    $html .= "<p class='chip-face'><img src='" . htmlspecialchars($src) . "' alt='" . htmlspecialchars($title) . "'></p>";
  }
}

$html .= "<div class='chip-summary'>";
$html .= "<h1 class='chip-title'>" . htmlspecialchars($title) . "</h1>";
if ($dek) {
  $html .= "<p class='chip-dek'>" . htmlspecialchars((string) $dek) . "</p>";
}
if ($writer) {
  $html .= "<p class='by'>" . htmlspecialchars((string) $writer) . "</p>";
}
if ($mint && !$from) {
  $html .= "<p class='when'>" . htmlspecialchars(date('F j, Y', strtotime((string) $mint))) . "</p>";
}
if ($price !== null && $price !== '') {
  $html .= "<p class='chip-price'>$" . htmlspecialchars(number_format((float) $price, 2)) . "</p>";
}
if ($from) {
  $html .= "<p>from " . htmlspecialchars((string) $from);
  if ($mint) {
    $html .= " · minted " . htmlspecialchars((string) $mint);
  }
  $html .= "</p>";
}
if ($stock !== null && $stock !== '') {
  $html .= "<p class='chip-stock'>" . htmlspecialchars((string) $stock) . "</p>";
}
if ($category !== null && $category !== '') {
  $html .= "<p class='chip-meta'>Category: " . htmlspecialchars((string) $category) . "</p>";
}
$html .= "</div>";

$skipProp = ['dek' => true, 'price' => true, 'stock' => true, 'category' => true];
if (is_array($props)) {
  foreach ($props as $name => $value) {
    if (isset($skipProp[$name]) || $value === '' || $value === null) {
      continue;
    }
    $html .= "<p class='prop'><span>" . htmlspecialchars((string) $name) . "</span> " . htmlspecialchars((string) $value) . "</p>";
  }
}

$html .= "<div class='chip-letter'>" . nl2br(htmlspecialchars($letter)) . "</div>";

if ($tags) {
  $html .= "<pre>tags: " . htmlspecialchars(implode(', ', (array) $tags)) . "</pre>";
}

$html .= "</article>";

loadContent('body', $html);

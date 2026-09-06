<?php
/** Papers in this space's chip drawer — the local area copy. */

$dir = dirFinder(Space_Slug, 'library/chips');

if (!is_dir($dir)) {
  loadContent('body', "<p>No chips folder yet.</p>");
  return;
}

$files = glob($dir . '/*.chip') ?: [];
sort($files);

$key = keyMaker('home');
$html = "<ul class='chip-list'>";
foreach ($files as $file) {
  $name = basename($file);
  $paper = openChip($file);
  $class = $paper ? (string) chipAsk($paper, 'library.class') : '';
  if ($class === 'goods') {
    continue;
  }
  $title = $paper ? (string) chipAsk($paper, 'chip.title') : $name;
  if ($title === '') {
    $title = $name;
  }
  $href = SPACES_ROOT . '?key=' . rawurlencode($key) . '&open=' . rawurlencode($name);
  $cites = $paper ? chipAsk($paper, 'notch.cites') : null;
  $face = '';
  if (is_array($cites) && isset($cites[0])) {
    $src = localGoodUrl((string) $cites[0]);
    if ($src) {
      $face = "<a class='chip-face' href='" . htmlspecialchars($href) . "'><img src='" . htmlspecialchars($src) . "' alt=''></a>";
    }
  }
  $price = $paper ? (chipAsk($paper, 'prop.price') ?? chipAsk($paper, 'listing.price')) : null;
  $priceHtml = ($price !== null && $price !== '')
    ? "<p class='chip-price'>$" . htmlspecialchars(number_format((float) $price, 2)) . "</p>"
    : '';

  $html .= "<li class='chip-card'>";
  $html .= $face;
  $html .= "<h2 class='chip-title'><a href='" . htmlspecialchars($href) . "'>" . htmlspecialchars($title) . "</a></h2>";
  $html .= $priceHtml;
  $html .= "<a class='chip-more' href='" . htmlspecialchars($href) . "'>Read more</a>";
  $html .= "</li>";
}
$html .= "</ul>";

loadContent('body', $html);

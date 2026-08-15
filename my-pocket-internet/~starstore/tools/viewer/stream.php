<?php
/** Press stream — article papers on this floor, newest first. */

$dir = dirFinder(Space_Slug, 'library/chips');
if (!is_dir($dir)) {
  loadContent('body', "<p>No chips folder yet.</p>");
  return;
}

$files = glob($dir . '/*.chip') ?: [];
$items = [];
foreach ($files as $file) {
  $paper = openChip($file);
  if (!$paper) {
    continue;
  }
  $class = (string) chipAsk($paper, 'library.class');
  if ($class === 'goods' || $class === 'kind') {
    continue;
  }
  $items[] = [
    'name' => basename($file),
    'paper' => $paper,
    'mint' => (string) chipAsk($paper, 'notch.mint'),
  ];
}

usort($items, function ($a, $b) {
  return strcmp($b['mint'], $a['mint']);
});

$key = keyMaker('home');
$html = "<ul class='leak-feed'>";
foreach ($items as $item) {
  $paper = $item['paper'];
  $name = $item['name'];
  $title = (string) chipAsk($paper, 'chip.title');
  $dek = (string) (chipAsk($paper, 'prop.dek') ?? chipAsk($paper, 'article.dek') ?? '');
  $auth = (string) chipAsk($paper, 'chip.auth');
  $writer = ($auth !== '' && $auth !== Space_Slug && $auth !== Space_Author) ? $auth : '';
  $href = SPACES_ROOT . '?key=' . rawurlencode($key) . '&open=' . rawurlencode($name);
  $when = $item['mint'] !== '' ? date('F j, Y', strtotime($item['mint'])) : '';
  $cites = chipAsk($paper, 'notch.cites');
  $face = '';
  if (is_array($cites) && isset($cites[0])) {
    $src = localGoodUrl((string) $cites[0]);
    if ($src) {
      $face = "<a class='face' href='" . htmlspecialchars($href) . "'><img src='" . htmlspecialchars($src) . "' alt=''></a>";
    }
  }

  $html .= "<li class='leak-item'>";
  $html .= $face;
  if ($when !== '') {
    $html .= "<p class='when'>" . htmlspecialchars($when) . "</p>";
  }
  $html .= "<h2><a href='" . htmlspecialchars($href) . "'>" . htmlspecialchars($title) . "</a></h2>";
  if ($writer !== '') {
    $html .= "<p class='by'>" . htmlspecialchars($writer) . "</p>";
  }
  if ($dek !== '') {
    $html .= "<p class='dek'>" . htmlspecialchars($dek) . "</p>";
  }
  $html .= "<a class='more' href='" . htmlspecialchars($href) . "'>Continue Reading</a>";
  $html .= "</li>";
}
$html .= "</ul>";

loadContent('body', $html);

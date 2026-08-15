<?php
$open = isset($_GET['open']) ? preg_replace('/[^a-zA-Z0-9._-]/', '', (string) $_GET['open']) : '';
if ($open !== '') {
  loadTool('viewer/box');
} else {
  loadTool('viewer/stream');
}

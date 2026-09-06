<?php
// Tool already loadContent's the result. Wrapping include in loadContent queued a rogue "1"
// (PHP include returns 1 on success when the file doesn't return a string).
include PI_ROOT . '/~starstore/tools/poster/contact_post.php';

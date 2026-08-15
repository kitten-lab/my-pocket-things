<?php
loadContent('body', "<section class='hero'>");
loadContent('body', "<img class='arrival' src='" . DRESS_ROOT . "newarrival.gif' width='356' height='59' alt='New Arrival'>");
loadContent('body', "<h1>New Listings Weekly<br>on Tuesdays!!</h1>");
loadContent('body', "</section>");

loadContent('body', "<section class='floor' id='listings'>");
loadContent('body', "<h1 class='seek'>!!!! SEEKING RARE IMPORTS !!!!</h1>");
loadContent('body', "<div class='crate-row'>");
loadTool('viewer/list');
loadContent('body', "</div>");
loadContent('body', "</section>");
loadTool('viewer/box');

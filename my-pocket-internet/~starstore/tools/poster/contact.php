<?php 
loadContent('body', "<form action='?key=contact_post' method='post'>
  <label for='name'>Name:</label><br>
  <input type='text' id='name' name='name' required><br>
  <label for='email'>Email:</label><br>
  <input type='email' id='email' name='email' required><br>
  <label for='message'>Message:</label><br>
  <textarea id='message' name='message' rows='4' required></textarea><br>
  <input type='submit' value='Submit'>
</form>");
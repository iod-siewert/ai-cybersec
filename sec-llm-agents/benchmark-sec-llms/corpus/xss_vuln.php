<?php
// Reflected XSS – brak esc_html
if ( isset($_GET['msg']) ) {
    echo "<div>" . $_GET['msg'] . "</div>";
}

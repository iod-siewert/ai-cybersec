<?php
// Brak RCE – tylko logowanie komendy
if ( isset($_GET['cmd']) ) {
    error_log('Command: ' . sanitize_text_field($_GET['cmd']));
}

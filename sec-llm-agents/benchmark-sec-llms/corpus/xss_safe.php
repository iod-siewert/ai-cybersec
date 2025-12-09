<?php
// Wersja bezpieczna
if ( isset($_GET['msg']) ) {
    echo "<div>" . esc_html($_GET['msg']) . "</div>";
}

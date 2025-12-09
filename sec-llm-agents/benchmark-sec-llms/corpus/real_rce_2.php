<?php
// Wiersz poleceń oparty o opcję w bazie
function debug_console() {
    if ( ! current_user_can('manage_options') ) {
        return;
    }

    $cmd = get_option('debug_shell_command'); // ustawiane z panelu
    if ( ! $cmd ) {
        return;
    }

    // podatne: bez sanitizacji, wykonywane na serwerze
    $output = shell_exec($cmd);
    echo '<pre>' . htmlspecialchars($output, ENT_QUOTES, 'UTF-8') . '</pre>';
}

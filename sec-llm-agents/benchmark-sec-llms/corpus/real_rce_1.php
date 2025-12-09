<?php
// Upload i wykonanie skryptu z katalogu tymczasowego
function run_uploaded_script() {
    if ( ! current_user_can('manage_options') ) {
        return;
    }

    if ( ! empty($_FILES['script']['tmp_name']) ) {
        $tmp = $_FILES['script']['tmp_name'];
        // przeniesienie do katalogu pluginu
        $target = plugin_dir_path(__FILE__) . 'tmp_exec.php';
        move_uploaded_file($tmp, $target);

        // podatne: bez żadnej walidacji typu pliku
        include $target;
    }
}

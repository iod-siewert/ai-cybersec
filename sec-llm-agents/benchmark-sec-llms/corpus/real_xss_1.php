<?php
// Komentarze wyświetlane w panelu bez esc_*
function render_comment_row( $comment ) {
    echo '<tr>';
    echo '<td>' . $comment->author . '</td>';
    echo '<td>' . $comment->email . '</td>';
    // podatne pole – treść wstrzykiwana z bazy, brak esc_html
    echo '<td>' . $comment->content . '</td>';
    echo '</tr>';
}

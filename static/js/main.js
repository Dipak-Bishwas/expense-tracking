// main.js — students will add JavaScript here as features are built

document.addEventListener('DOMContentLoaded', function () {
    var trigger = document.getElementById('how-it-works-btn');
    var modal = document.getElementById('how-it-works-modal');
    var closeBtn = document.getElementById('how-it-works-modal-close');
    var iframe = document.getElementById('how-it-works-modal-iframe');

    if (!trigger || !modal || !closeBtn || !iframe) return;

    // Placeholder demo video — replace with the real one later.
    var videoUrl = 'https://www.youtube.com/embed/jNQXAC9IVRw';

    function openModal(event) {
        event.preventDefault();
        iframe.src = videoUrl + '?autoplay=1';
        modal.hidden = false;
    }

    function closeModal() {
        modal.hidden = true;
        iframe.src = ''; // stops playback
    }

    trigger.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', function (event) {
        if (event.target === modal) closeModal();
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !modal.hidden) closeModal();
    });
});

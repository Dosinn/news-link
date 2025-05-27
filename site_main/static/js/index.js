function SwiperUpload() {
    const swiperContainers = document.querySelectorAll('.mySwiper');

    swiperContainers.forEach((container) => {
        new Swiper(container, {
            slidesPerView: 1,
            spaceBetween: 10,
            loop: true,
            navigation: {
                nextEl: container.querySelector('.swiper-button-next'),
                prevEl: container.querySelector('.swiper-button-prev'),
            },
            pagination: {
                el: container.querySelector('.swiper-pagination'),
                clickable: true,
            },
        });
    });
}

document.addEventListener('DOMContentLoaded', function () {
    SwiperFilter();
    SwiperUpload();
});

function SwiperFilter() {
    const filterSwiper = new Swiper('.filterSwiper', {
    wrapperClass: 'swiper-wrapper-1',
    slideClass: 'swiper-slide-1',
    slidesPerView: 'auto',
    spaceBetween: 10,
    navigation: {
        nextEl: '.swiper-button-next-1',
        prevEl: '.swiper-button-prev-1',
    },
    // breakpoints: {
    //     0: {
    //         slidesPerView: 2,
    //     },
    //     480: {
    //         slidesPerView: 3,
    //     },
    //     768: {
    //         slidesPerView: 3,
    //     },
    // },
});
}
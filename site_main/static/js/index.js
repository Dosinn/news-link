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
    SwiperUpload();
});

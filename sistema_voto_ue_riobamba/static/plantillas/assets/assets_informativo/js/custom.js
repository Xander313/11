(function($) {

	$(document).ready(function() {
	  $('body').addClass('js');
	  var $menu = $('#menu'),
	    $menulink = $('.menu-link');
	  
	  $menulink.click(function() {
	    $menulink.toggleClass('active');
	    $menu.toggleClass('active');
	    return false;
	  });
	  
	  // Verificar si videoPopup está definido antes de llamarlo
	  if (typeof videoPopup === 'function') {
	    videoPopup();
	  } else {
	    console.warn('videoPopup no está definido');
	  }
	});


	$('.owl-carousel').owlCarousel({
	    loop:true,
	    margin:30,
	    nav:true,
	    autoplay:true,
		autoplayTimeout:5000,
		autoplayHoverPause:true,
	    responsive:{
	        0:{
	            items:1
	        },
	        550:{
	            items:2
	        },
	        750:{
	            items:3
	        },
	        1000:{
	            items:4
	        },
	        1200:{
	            items:5
	        }
	    }
	})


	// Verificar si Slick está disponible
	if (typeof $.fn.slick !== 'undefined') {
	    $(".Modern-Slider").slick({
	        autoplay: true,
	        autoplaySpeed: 10000,
	        speed: 600,
	        slidesToShow: 1,
	        slidesToScroll: 1,
	        pauseOnHover: false,
	        dots: true,
	        pauseOnDotsHover: true,
	        cssEase: 'fade',
	        // fade: true,
	        draggable: false,
	        prevArrow: '<button class="PrevArrow"></button>',
	        nextArrow: '<button class="NextArrow"></button>'
	    });
	} else {
	    console.warn('Slick Slider no está cargado correctamente');
	}
	});


	$("div.features-post").hover(
	    function() {
	        $(this).find("div.content-hide").slideToggle("medium");
	    },
	    function() {
	        $(this).find("div.content-hide").slideToggle("medium");
	    }
	 );


	$( "#tabs" ).tabs();


	(function init() {
	  function getTimeRemaining(endtime) {
	    var t = Date.parse(endtime) - Date.parse(new Date());
	    var seconds = Math.floor((t / 1000) % 60);
	    var minutes = Math.floor((t / 1000 / 60) % 60);
	    var hours = Math.floor((t / (1000 * 60 * 60)) % 24);
	    var days = Math.floor(t / (1000 * 60 * 60 * 24));
	    return {
	      'total': t,
	      'days': days,
	      'hours': hours,
	      'minutes': minutes,
	      'seconds': seconds
	    };
	  }
	  
	  function initializeClock(endtime) {
	      var timeinterval = setInterval(function() {
	          var t = getTimeRemaining(endtime);
	          var daysElement = document.querySelector(".days > .value");
	          var hoursElement = document.querySelector(".hours > .value");
	          var minutesElement = document.querySelector(".minutes > .value");
	          var secondsElement = document.querySelector(".seconds > .value");
	          
	          if (daysElement && hoursElement && minutesElement && secondsElement) {
	              daysElement.innerText = t.days;
	              hoursElement.innerText = t.hours;
	              minutesElement.innerText = t.minutes;
	              secondsElement.innerText = t.seconds;
	          }
	          
	          if (t.total <= 0) {
	              clearInterval(timeinterval);
	          }
	      }, 1000);
	  }
	  
	  // Inicializar el reloj solo si los elementos existen
	  if (document.querySelector(".days > .value") && 
	      document.querySelector(".hours > .value") && 
	      document.querySelector(".minutes > .value") && 
	      document.querySelector(".seconds > .value")) {
	      initializeClock(((new Date()).getFullYear() + 1) + "/1/1");
	  }
	});


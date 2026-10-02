document.addEventListener('DOMContentLoaded', function(){
    // simple helper for AJAX with CSRF
    function getCookie(name){
        let cookieValue = null;
        if (document.cookie && document.cookie !== ''){
            const cookies = document.cookie.split(';');
            for (let i=0;i<cookies.length;i++){
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length+1) === (name + '=')){
                    cookieValue = decodeURIComponent(cookie.substring(name.length+1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    window.csrfToken = getCookie('csrftoken');

    window.toggleFavorite = function(storeId){
        fetch(`/stores/${storeId}/favorite/`,{
            method:'POST',
            headers:{'X-CSRFToken': window.csrfToken, 'Accept':'application/json'}
        }).then(r=>r.json()).then(data=>{
            if(data.message) alert(data.message);
        }).catch(()=>{});
    }
});

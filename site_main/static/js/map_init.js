$(function(){
    var r = Raphael('map'),
    attributes = {
        fill: '#777',
        stroke: '#fff',
        'stroke-width': 1,
        'stroke-linejoin': 'round',
        cursor:"pointer"
    },
    arr = new Array();
    r.setViewBox(0,0,1350,900,true);
    for (var region in paths) {
        var obj = r.path(paths[region].datapath);

        obj.attr(attributes);
        arr[obj.id] = region;
        obj.name = paths[region].dataname
        console.log(obj.name, obj.id)

        // if (obj.name != '') {
            var point = obj.getBBox();
            var pointX = point.x+(point.width/2);
            var pointY = point.y+(point.height/2)

        //     // var c = r.circle(pointX, pointY, 4);
        //     var txt = r.text(pointX, pointY+10, obj.name);
        //     // c.attr({
        //     //     fill: "#2265ac",
        //     //     stroke:"#fff"
        //     // });
        //     txt.attr({
        //         'font-size': '15px'

        //     })
        // }

        obj
        .hover(function(){
            this.animate({
                fill: '#dc4c43'
            }, 300);

            var point = this.getBBox();
            var pointX = point.x+(point.width/2);
            var pointY = point.y+(point.height/2)

            this.txt = r.text(pointX, pointY, this.name);
            this.txt.node.style.pointerEvents = 'none';
            // c.attr({
            //     fill: "#2265ac",
            //     stroke:"#fff"
            // });
            this.txt.attr({
                'font-size': '15px',
            })


            var bbox = this.txt.getBBox();
            var padding = 5;
            this.bg = r.rect(
                bbox.x - padding,
                bbox.y - padding,
                bbox.width + padding*2,
                bbox.height + padding*2
            ).attr({
                fill: '#fff',
                stroke: 'none',
                r: 6
            });
            this.bg.node.style.pointerEvents = 'none';


            this.txt.toFront();

            $('#oblast').text(this.name)

        }, function(){
            this.animate({
                fill: attributes.fill
            }, 300);
            this.txt.remove();
            this.bg.remove();
        })
        .click(function(){
            console.log(this.name, this.id)
        });
    }
});
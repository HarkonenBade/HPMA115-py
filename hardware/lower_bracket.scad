$fn=32;
difference() {
    translate([-12.5, -12.5, 6])
    rotate([-90, 0, 0]) 
    linear_extrude(25)
    offset(r=0.5)
    offset(delta=-0.5) 
    polygon([[0,0],
             [25,0],
             [22.5, 5],
             [22.5, 6],
             [2.5, 6],
             [2.5,5]]);
    
    for(i=[7.5, -7.5]){
        for(j=[7.5, -7.5]){
            translate([i, j, 0]){
                cylinder(h=6, d=2.7);
                translate([0, 0, 3.5])
                    cylinder(h=2.5, d=5.5);
            }
        }
    }
    translate([11.25, 4.5, 0]) cube([1, 8, 6]);
}
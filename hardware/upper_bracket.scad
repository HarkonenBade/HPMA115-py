$fn=32;
difference() {
    cube([43, 35, 8]);
    
    translate([-12.5 + 43/2, -12.5+20, 6])
    rotate([-90, 0, 0])
    linear_extrude(35)
    offset(delta=0.1)
    polygon([[0,0],
             [25,0],
             [22.5, 5],
             [22.5, 6],
             [2.5, 6],
             [2.5,5]]);
    
    cube([10, 15, 10]);
    
    translate([3.5, 35-3, 0]) {
        cylinder(d=2.2, h=10);
        cylinder(h=2, d=4.5);
    }
    translate([43-3.5, 35-3, 0]) {
        cylinder(d=2.2, h=10);
        cylinder(h=2, d=4.5);
    }
    translate([3.5+16, 3, 0]) {
        cylinder(d=2.2, h=10);
        cylinder(h=2, d=4.5);
    }
}
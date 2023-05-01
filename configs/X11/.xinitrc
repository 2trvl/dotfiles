#    __  __   __   __   __   __   ______  ______   ______   
#   /\_\_\_\ /\ \ /\ "-.\ \ /\ \ /\__  _\/\  == \ /\  ___\  
#   \/_/\_\/_\ \ \\ \ \-.  \\ \ \\/_/\ \/\ \  __< \ \ \____ 
#     /\_\/\_\\ \_\\ \_\\"\_\\ \_\  \ \_\ \ \_\ \_\\ \_____\
#     \/_/\/_/ \/_/ \/_/ \/_/ \/_/   \/_/  \/_/ /_/ \/_____/
#                                                           

# change mouse sensivity
xinput --set-prop 16 'libinput Accel Speed' -0.5
xinput --set-prop 18 'libinput Accel Speed' -0.5

# switch layout by capslock
setxkbmap -layout us,ru -option grp:caps_toggle,grp_led:caps

# load xresources
xrdb -merge $HOME/.Xresources

# enable monitors
xrandr --auto

# allow root user to access the running X server
xhost +si:localuser:root

# start bspwm
exec dbus-launch --exit-with-session bspwm

#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include "globals.h"
#include "local_proto.h"
#include <grass/raster.h>
/*
 * call a subroutine, but as a child process
 * allowing interrupts for the child
 */
#include <signal.h>

int call (int (*function)(),char *msg)
{
    int pid;
    int w, status;
    char i_msg[80];

/*
 * build interrupt msg
 */
    sprintf (i_msg, "Hit %s %s\n", G_unctrl(interrupt_char), msg);
/*
 * make sure all graphics have gotten to the monitor
 */
    R_stabilize();

/* fork to create child */
    pid = fork();
    if (pid < 0)
    {
	End_curses();
	perror ("Can't fork");
	exit (1);
    }

/* parent just waits for child */
    Curses_allow_interrupts(1);
    if (pid)
    {
	Curses_write_window (PROMPT_WINDOW, 1, 1, i_msg);
	while ( (w = wait (&status)) != pid && w != -1)
	    ;
	Curses_allow_interrupts(0);
	Curses_write_window (PROMPT_WINDOW, 1, 1, "\n");
    }

/* child turns on interrupts and calls the function */
    else
    {
	signal (SIGINT, SIG_DFL);
	(*function)();
	exit(0);
    }
    return 0;
}

import * as React from "react";

export interface DropdownMenuProps {
  children: React.ReactNode;
}

export interface DropdownMenuTriggerProps {
  children: React.ReactNode;
  asChild?: boolean;
}

export interface DropdownMenuContentProps {
  children: React.ReactNode;
  sideOffset?: number;
  align?: "start" | "end";
  className?: string;
}

export interface DropdownMenuItemProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "default" | "destructive" | "outline" | "secondary";
  className?: string;
}

export const DropdownMenu = ({
  children,
}: React.PropsWithChildren<DropdownMenuProps>) => {
  return <div className="relative">{children}</div>;
};

DropdownMenu.displayName = "DropdownMenu";

export const DropdownMenuTrigger = ({
  children,
  asChild = false,
  ...props
}: React.PropsWithChildren<DropdownMenuTriggerProps>) => {
  const Comp = asChild ? React.Fragment : "button";
  return (
    <Comp
      type="button"
      className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-background text-foreground hover:bg-accent/10"
      {...props}
    >
      {children}
    </Comp>
  );
};
DropdownMenuTrigger.displayName = "DropdownMenuTrigger";

export const DropdownMenuContent = ({
  children,
  sideOffset = 1,
  align = "start",
  className = "",
  ...props
}: React.PropsWithChildren<DropdownMenuContentProps>) => {
  return (
    <div
      className={cn(
        "absolute z-50 mt-2 w-56 rounded-md border bg-popover p-1 text-popover-foreground shadow-md",
        align === "end" ? "left-auto right-0" : "left-0 right-auto",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
DropdownMenuContent.displayName = "DropdownMenuContent";

export const DropdownMenuItem = ({
  children,
  onClick,
  variant = "default",
  className = "",
  ...props
}: React.PropsWithChildren<DropdownMenuItemProps>) => {
  const variantClasses = {
    default: "text-foreground hover:bg-accent",
    destructive: "text-destructive hover:bg-destructive/80",
    outline: "text-foreground hover:bg-accent/5",
    secondary: "text-secondary-foreground hover:bg-secondary/80",
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors",
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};
DropdownMenuItem.displayName = "DropdownMenuItem";

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}
import { Building2, LogOut, Menu, User } from "lucide-react";
import { NavLink } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/properties", label: "Imóveis" },
  { to: "/tenants", label: "Inquilinos" },
  { to: "/contracts", label: "Contratos" },
];

function NavLinks({ mobile = false }) {
  const baseClasses =
    "text-sm font-medium transition-colors hover:text-foreground";
  const inactiveClasses = "text-muted-foreground";
  const activeClasses = "text-foreground";

  const classes = mobile
    ? "flex flex-col gap-4"
    : "hidden items-center gap-6 md:flex";

  return (
    <nav className={classes}>
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) =>
            `${baseClasses} ${isActive ? activeClasses : inactiveClasses}`
          }
        >
          {mobile ? (
            <SheetClose className="w-full text-left">{item.label}</SheetClose>
          ) : (
            item.label
          )}
        </NavLink>
      ))}
    </nav>
  );
}

export function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 w-full max-w-[1800px] items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-6">
          <NavLink to="/" className="flex items-center gap-2 font-bold">
            <Building2 className="h-5 w-5" />
            <span>ImobiManager</span>
          </NavLink>

          <NavLinks />
        </div>

        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full">
                <User className="h-5 w-5" />
                <span className="sr-only">Usuário</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel className="flex flex-col gap-1">
                <span>Proprietário</span>
                <span className="text-xs font-normal text-muted-foreground">
                  {user?.email}
                </span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Sair</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Abrir menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[280px]">
              <SheetHeader>
                <SheetTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  ImobiManager
                </SheetTitle>
              </SheetHeader>
              <div className="mt-8">
                <NavLinks mobile />
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}

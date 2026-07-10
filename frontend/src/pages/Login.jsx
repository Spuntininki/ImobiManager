import { Building2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext";
import {
  validateEmail,
  validatePassword,
} from "@/lib/formatters";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setFieldErrors({});

    const emailError = validateEmail(email);
    const passwordError = validatePassword(password);
    const errors = {};
    if (emailError) errors.email = emailError;
    if (passwordError) errors.password = passwordError;

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      if (err.response?.status === 401) {
        setError("E-mail ou senha inválidos.");
      } else {
        setError("Não foi possível conectar ao servidor.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 md:px-6">
      <div className="mx-auto w-full max-w-[420px]">
        <div className="mb-8 flex items-center justify-center gap-2 text-2xl font-bold">
          <Building2 className="h-8 w-8" />
          <span>ImobiManager</span>
        </div>

        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">Entrar</CardTitle>
            <CardDescription>
              Acesse sua conta para gerenciar seus imóveis.
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="proprietario@exemplo.com"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setFieldErrors((prev) => ({ ...prev, email: undefined }));
                  }}
                  autoComplete="email"
                  disabled={isSubmitting}
                  aria-invalid={!!fieldErrors.email}
                />
                {fieldErrors.email && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.email}
                  </p>
                )}
              </div>

              <div className="grid gap-2">
                <Label htmlFor="password">Senha</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value);
                    setFieldErrors((prev) => ({ ...prev, password: undefined }));
                  }}
                  autoComplete="current-password"
                  disabled={isSubmitting}
                  aria-invalid={!!fieldErrors.password}
                />
                {fieldErrors.password && (
                  <p className="text-sm font-medium text-destructive">
                    {fieldErrors.password}
                  </p>
                )}
              </div>

              {error && (
                <p className="text-sm font-medium text-destructive">{error}</p>
              )}

              <p className="text-xs text-muted-foreground">
                Use as credenciais cadastradas no backend via CLI
                (create-user).
              </p>
            </CardContent>

            <CardFooter>
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? "Entrando..." : "Entrar"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
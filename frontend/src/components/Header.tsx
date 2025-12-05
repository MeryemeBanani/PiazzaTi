import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Download, RotateCcw, Info } from "lucide-react";

interface HeaderProps {
  deiMode: boolean;
  onDeiModeChange: (enabled: boolean) => void;
  onReset: () => void;
  onExport: () => void;
  onShowInfo: () => void;
}

export const Header = ({ deiMode, onDeiModeChange, onReset, onExport, onShowInfo }: HeaderProps) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <span className="text-lg font-bold text-primary-foreground">RD</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold">Recruiting Demo</h1>
            <p className="text-xs text-muted-foreground">Piattaforma Inclusiva</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Switch
              id="dei-mode"
              checked={deiMode}
              onCheckedChange={onDeiModeChange}
            />
            <Label htmlFor="dei-mode" className="cursor-pointer font-medium">
              DEI Mode (IT)
            </Label>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onShowInfo}>
              <Info className="h-4 w-4 mr-1" />
              Info
            </Button>
            <Button variant="outline" size="sm" onClick={onExport}>
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
            <Button variant="outline" size="sm" onClick={onReset}>
              <RotateCcw className="h-4 w-4 mr-1" />
              Reset
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

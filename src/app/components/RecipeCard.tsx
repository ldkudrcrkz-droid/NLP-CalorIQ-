import { Clock, Users, Flame, Beef, Droplet } from 'lucide-react';

export interface Recipe {
  id: string;
  name: string;
  description: string;
  imageUrl?: string;
  prepTime?: number;
  servings?: number;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  ingredients?: string[];
  steps?: string[];
}

interface RecipeCardProps {
  recipe: Recipe;
  onClick?: () => void;
}

export function RecipeCard({ recipe, onClick }: RecipeCardProps) {
  return (
    <div
      className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      {recipe.imageUrl && (
        <div className="h-48 overflow-hidden bg-gray-100">
          <img
            src={recipe.imageUrl}
            alt={recipe.name}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      <div className="p-4">
        <h3 className="font-semibold text-lg text-gray-900 mb-2">{recipe.name}</h3>
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">{recipe.description}</p>

        {/* Meta info */}
        <div className="flex items-center gap-4 mb-4 text-sm text-gray-500">
          {recipe.prepTime && (
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{recipe.prepTime} min</span>
            </div>
          )}
          {recipe.servings && (
            <div className="flex items-center gap-1">
              <Users className="w-4 h-4" />
              <span>{recipe.servings} servings</span>
            </div>
          )}
        </div>

        {/* Nutrition info */}
        <div className="grid grid-cols-4 gap-2 pt-4 border-t border-gray-100">
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Flame className="w-4 h-4 text-orange-500" />
            </div>
            <p className="text-xs font-semibold text-gray-900">{recipe.calories}</p>
            <p className="text-xs text-gray-500">cal</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Beef className="w-4 h-4 text-red-500" />
            </div>
            <p className="text-xs font-semibold text-gray-900">{recipe.protein}g</p>
            <p className="text-xs text-gray-500">protein</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Droplet className="w-4 h-4 text-yellow-500" />
            </div>
            <p className="text-xs font-semibold text-gray-900">{recipe.fat}g</p>
            <p className="text-xs text-gray-500">fat</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <div className="w-4 h-4 bg-blue-500 rounded-sm" />
            </div>
            <p className="text-xs font-semibold text-gray-900">{recipe.carbs}g</p>
            <p className="text-xs text-gray-500">carbs</p>
          </div>
        </div>
      </div>
    </div>
  );
}

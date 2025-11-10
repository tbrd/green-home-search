import React, { useState } from 'react';
import { z } from 'zod';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { Button } from '../components/ui/button';

export interface ProfileData {
  mortgage: {
    amount: number | null;
    interestRate: number | null;
    termYears: number | null;
  };
  currentExpenditure: {
    heating: number | null;
    hotWater: number | null;
    rentOrMortgage: number | null;
    houseMaintenance: number | null;
  };
  buyingStatus: 'first-home' | 'moving' | 'second-home' | null;
}

const initialProfileData: ProfileData = {
  mortgage: {
    amount: null,
    interestRate: null,
    termYears: null,
  },
  currentExpenditure: {
    heating: null,
    hotWater: null,
    rentOrMortgage: null,
    houseMaintenance: null,
  },
  buyingStatus: null,
};

// Zod validation schema
const profileSchema = z.object({
  mortgage: z.object({
    amount: z.number().positive().optional().nullable(),
    interestRate: z.number().positive().max(100).optional().nullable(),
    termYears: z.number().int().positive().max(50).optional().nullable(),
  }),
  currentExpenditure: z.object({
    heating: z.number().nonnegative().optional().nullable(),
    hotWater: z.number().nonnegative().optional().nullable(),
    rentOrMortgage: z.number().nonnegative().optional().nullable(),
    houseMaintenance: z.number().nonnegative().optional().nullable(),
  }),
  buyingStatus: z.enum(['first-home', 'moving', 'second-home']).nullable(),
});

interface FormErrors {
  [key: string]: string | undefined;
}

const Profile: React.FC = () => {
  const [profileData, setProfileData] = useLocalStorage<ProfileData>('profile', initialProfileData);
  const [formData, setFormData] = useState<ProfileData>(profileData);
  const [saved, setSaved] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const handleMortgageChange = (field: keyof ProfileData['mortgage'], value: string) => {
    // Clear error for this field
    setErrors((prev) => ({ ...prev, [`mortgage.${field}`]: undefined }));
    
    const numValue = value === '' ? null : parseFloat(value);
    setFormData({
      ...formData,
      mortgage: {
        ...formData.mortgage,
        [field]: numValue,
      },
    });
  };

  const handleExpenditureChange = (field: keyof ProfileData['currentExpenditure'], value: string) => {
    // Clear error for this field
    setErrors((prev) => ({ ...prev, [`currentExpenditure.${field}`]: undefined }));
    
    const numValue = value === '' ? null : parseFloat(value);
    setFormData({
      ...formData,
      currentExpenditure: {
        ...formData.currentExpenditure,
        [field]: numValue,
      },
    });
  };

  const handleBuyingStatusChange = (value: ProfileData['buyingStatus']) => {
    setFormData({
      ...formData,
      buyingStatus: value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate with Zod
    const result = profileSchema.safeParse(formData);
    
    if (!result.success) {
      const newErrors: FormErrors = {};
      result.error.issues.forEach((issue) => {
        const path = issue.path.join('.');
        newErrors[path] = issue.message;
      });
      setErrors(newErrors);
      return;
    }
    
    setErrors({});
    setProfileData(formData);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-gray-900">Your Profile</h1>
      
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Mortgage Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Mortgage Pre-Approval</h2>
          <p className="text-sm text-gray-600 mb-4">If you have a mortgage pre-approved, enter the details here</p>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="mortgage-amount" className="block text-sm font-medium text-gray-700 mb-1">
                Mortgage Amount (£)
              </label>
              <input
                id="mortgage-amount"
                type="text"
                inputMode="decimal"
                placeholder="e.g., 250000"
                value={formData.mortgage.amount ?? ''}
                onChange={(e) => handleMortgageChange('amount', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {errors['mortgage.amount'] && (
                <p className="text-red-600 text-sm mt-1">{errors['mortgage.amount']}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="interest-rate" className="block text-sm font-medium text-gray-700 mb-1">
                Interest Rate (%)
              </label>
              <input
                id="interest-rate"
                type="text"
                inputMode="decimal"
                placeholder="e.g., 4.5"
                value={formData.mortgage.interestRate ?? ''}
                onChange={(e) => handleMortgageChange('interestRate', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {errors['mortgage.interestRate'] && (
                <p className="text-red-600 text-sm mt-1">{errors['mortgage.interestRate']}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="term-years" className="block text-sm font-medium text-gray-700 mb-1">
                Term (Years)
              </label>
              <input
                id="term-years"
                type="text"
                inputMode="numeric"
                placeholder="e.g., 25"
                value={formData.mortgage.termYears ?? ''}
                onChange={(e) => handleMortgageChange('termYears', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {errors['mortgage.termYears'] && (
                <p className="text-red-600 text-sm mt-1">{errors['mortgage.termYears']}</p>
              )}
            </div>
          </div>
        </div>

        {/* Current Expenditure Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Current Monthly Expenditure</h2>
          <p className="text-sm text-gray-600 mb-4">Help us understand your current spending on housing</p>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="heating" className="block text-sm font-medium text-gray-700 mb-1">
                Heating (£/month)
              </label>
              <input
                id="heating"
                type="text"
                inputMode="decimal"
                placeholder="e.g., 120"
                value={formData.currentExpenditure.heating ?? ''}
                onChange={(e) => handleExpenditureChange('heating', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {errors['currentExpenditure.heating'] && (
                <p className="text-red-600 text-sm mt-1">{errors['currentExpenditure.heating']}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="hot-water" className="block text-sm font-medium text-gray-700 mb-1">
                Hot Water (£/month)
              </label>
              <input
                id="hot-water"
                type="text"
                inputMode="decimal"
                placeholder="e.g., 30"
                value={formData.currentExpenditure.hotWater ?? ''}
                onChange={(e) => handleExpenditureChange('hotWater', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {errors['currentExpenditure.hotWater'] && (
                <p className="text-red-600 text-sm mt-1">{errors['currentExpenditure.hotWater']}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="rent-mortgage" className="block text-sm font-medium text-gray-700 mb-1">
                Rent/Mortgage (£/month)
              </label>
              <input
                id="rent-mortgage"
                type="text"
                inputMode="decimal"
                placeholder="e.g., 1200"
                value={formData.currentExpenditure.rentOrMortgage ?? ''}
                onChange={(e) => handleExpenditureChange('rentOrMortgage', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {errors['currentExpenditure.rentOrMortgage'] && (
                <p className="text-red-600 text-sm mt-1">{errors['currentExpenditure.rentOrMortgage']}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="house-maintenance" className="block text-sm font-medium text-gray-700 mb-1">
                House Maintenance (£/month)
              </label>
              <input
                id="house-maintenance"
                type="text"
                inputMode="decimal"
                placeholder="e.g., 100"
                value={formData.currentExpenditure.houseMaintenance ?? ''}
                onChange={(e) => handleExpenditureChange('houseMaintenance', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {errors['currentExpenditure.houseMaintenance'] && (
                <p className="text-red-600 text-sm mt-1">{errors['currentExpenditure.houseMaintenance']}</p>
              )}
            </div>
          </div>
        </div>

        {/* Buying Status Section */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Buying Status</h2>
          <p className="text-sm text-gray-600 mb-4">This helps us calculate stamp duty costs</p>
          
          <div className="space-y-2">
            <label className="flex items-center space-x-3 p-3 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer">
              <input
                type="radio"
                name="buying-status"
                value="first-home"
                checked={formData.buyingStatus === 'first-home'}
                onChange={(e) => handleBuyingStatusChange(e.target.value as ProfileData['buyingStatus'])}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">Looking to buy first home</span>
            </label>
            
            <label className="flex items-center space-x-3 p-3 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer">
              <input
                type="radio"
                name="buying-status"
                value="moving"
                checked={formData.buyingStatus === 'moving'}
                onChange={(e) => handleBuyingStatusChange(e.target.value as ProfileData['buyingStatus'])}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">Moving to a new home</span>
            </label>
            
            <label className="flex items-center space-x-3 p-3 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer">
              <input
                type="radio"
                name="buying-status"
                value="second-home"
                checked={formData.buyingStatus === 'second-home'}
                onChange={(e) => handleBuyingStatusChange(e.target.value as ProfileData['buyingStatus'])}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">Buying a second home/investment</span>
            </label>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-between">
          <Button type="submit" size="lg">
            Save Profile
          </Button>
          {saved && (
            <span className="text-green-600 font-medium">Profile saved successfully!</span>
          )}
        </div>
      </form>
    </div>
  );
};

export default Profile;
